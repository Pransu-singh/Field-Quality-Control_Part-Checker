const isSingleInstance = require("single-instance");
const single = new isSingleInstance("fqc-report-lock");

single.lock().then(() => {
  //console.log("✅ report_sender.js started (no other instance running)");
  // your cron code starts here
}).catch(() => {
  //console.log("❌ report_sender.js already running. Skipping...");
  process.exit(0); // exit silently
});

require("dotenv").config();
const cron = require("node-cron");
const nodemailer = require("nodemailer");
const { Client } = require("pg");
const ExcelJS = require("exceljs");
const fs = require("fs");
const path = require("path");

// PostgreSQL config
const dbClient = new Client({
  host: process.env.DB_HOST,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME,
  port: process.env.DB_PORT,
  options: "-c timezone=Asia/Kolkata"
});
dbClient.connect();

// Mail transporter
const transporter = nodemailer.createTransport({
  host: process.env.EMAIL_HOST,
  port: process.env.EMAIL_PORT,
  secure: false,
  auth: {
    user: process.env.EMAIL_USER,
    pass: process.env.EMAIL_PASS,
  },
  tls: { rejectUnauthorized: false },
});

// Convert timestamp to IST-formatted string
function formatDateIST(ts) {
  return new Date(ts).toLocaleString("en-GB", {
    timeZone: "Asia/Kolkata",
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  }).replace(",", "");
}

async function sendReport(shift = null) {
  const now = new Date();
  const dateStr = now.toLocaleDateString("en-GB").split("/").reverse().join("-");
  const displayDate = now.toLocaleDateString("en-GB");
  const subject = `VECV Dewas CWP-FQC Report For ${dateStr}` + (shift ? ` - Shift ${shift}` : "");

  const shiftClause = shift ? `AND shift = '${shift}'` : "";
  const query = `
    SELECT user_type, username, unit, location, timestamp, shift,
           crown_scan, pinion_scan, crown_id_no, pinion_id_no,
           crown_set_no, pinion_set_no, ed_no, set_match, part_match,
           overall_status, repeat_no
    FROM fqc_part_table
    WHERE DATE(timestamp) = CURRENT_DATE
    ${shiftClause}
  `;

  try {
    const result = await dbClient.query(query);

    result.rows.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

    const workbook = new ExcelJS.Workbook();
    const worksheet = workbook.addWorksheet("FQC Report");

    worksheet.columns = [
      { header: "sr.no.", key: "sr_no", width: 10 },
      { header: "user_type", key: "user_type", width: 15 },
      { header: "username", key: "username", width: 15 },
      { header: "unit", key: "unit", width: 15 },
      { header: "location", key: "location", width: 15 },
      { header: "timestamp", key: "timestamp", width: 22 },
      { header: "shift", key: "shift", width: 10 },
      { header: "crown_scan", key: "crown_scan", width: 25 },
      { header: "pinion_scan", key: "pinion_scan", width: 25 },
      { header: "crown_id_no", key: "crown_id_no", width: 15 },
      { header: "pinion_id_no", key: "pinion_id_no", width: 15 },
      { header: "crown_set_no", key: "crown_set_no", width: 15 },
      { header: "pinion_set_no", key: "pinion_set_no", width: 15 },
      { header: "ed_no", key: "ed_no", width: 15 },
      { header: "set_match", key: "set_match", width: 10 },
      { header: "part_match", key: "part_match", width: 10 },
      { header: "overall_status", key: "overall_status", width: 15 },
      { header: "repeat_no", key: "repeat_no", width: 10 },
    ];

    worksheet.getRow(1).eachCell(cell => {
      cell.fill = {
        type: 'pattern',
        pattern: 'solid',
        fgColor: { argb: 'D9E1F2' },
      };
    });

    if (result.rows.length > 0) {
      result.rows.forEach((row, index) => {
        const newRow = worksheet.addRow({
          sr_no: index + 1,
          ...row,
          timestamp: formatDateIST(row.timestamp),
        });

        const yesStyle = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'C6EFCE' } };
        const noStyle = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFC7CE' } };

        const colIndexes = {
          set_match: worksheet.getColumn("set_match").number,
          part_match: worksheet.getColumn("part_match").number,
          overall_status: worksheet.getColumn("overall_status").number,
          repeat_no: worksheet.getColumn("repeat_no").number,
        };

        newRow.getCell(colIndexes.set_match).fill = row.set_match?.toLowerCase() === 'yes' ? yesStyle : noStyle;
        newRow.getCell(colIndexes.part_match).fill = row.part_match?.toLowerCase() === 'yes' ? yesStyle : noStyle;
        newRow.getCell(colIndexes.overall_status).fill = row.overall_status?.toLowerCase() === 'ok' ? yesStyle : noStyle;

        if (row.repeat_no && Number(row.repeat_no) > 1) {
          newRow.getCell(colIndexes.repeat_no).fill = noStyle;
        }
      });
    } else {
      worksheet.addRow({
        sr_no: 1,
        user_type: "No Data",
        username: "",
        unit: "UNIT-1",
        location: "CWPFQC",
        timestamp: "",
        shift: shift || "",
        crown_scan: "",
        pinion_scan: "",
        crown_id_no: "",
        pinion_id_no: "",
        crown_set_no: "",
        pinion_set_no: "",
        ed_no: "",
        set_match: "",
        part_match: "",
        overall_status: "",
        repeat_no: "",
      });
    }

    const filename = `FQC_Report_${dateStr}_${shift || 'Day'}.xlsx`;
    const filePath = path.join(__dirname, filename);
    await workbook.xlsx.writeFile(filePath);

    const recipients = process.env.EMAIL_RECIPIENTS.split(',');

    const emailTable = `<p>Report summary available in attached Excel.</p>`;

    const mailOptions = {
      from: `"Quality Digitalization" <${process.env.EMAIL_USER}>`,
      to: recipients,
      subject,
      html: emailTable,
      attachments: [{ filename, path: filePath }],
    };

    transporter.sendMail(mailOptions, (error, info) => {
      if (error) {
        console.error("❌ Email error:", error.message);
      } else {
        console.log(`✅ Email sent for ${shift || "Day"}:`, info.response);
      }

      if (fs.existsSync(filePath)) fs.unlinkSync(filePath);
    });

  } catch (err) {
    console.error("❌ DB fetch error:", err.message);
  }
}

// Cron Jobs
cron.schedule("0 16 * * *", () => sendReport("A"), { timezone: "Asia/Kolkata" });
cron.schedule("0 0 * * *", () => sendReport("B"), { timezone: "Asia/Kolkata" });
cron.schedule("30 7 * * *", () => sendReport("C"), { timezone: "Asia/Kolkata" });
cron.schedule("0 9 * * *", () => sendReport(),     { timezone: "Asia/Kolkata" });

console.log("FQC Report Scheduler is running...");
