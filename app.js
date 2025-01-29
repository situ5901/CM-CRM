const express = require('express');
const session = require('express-session');
const { MongoClient } = require('mongodb');
const multer = require('multer');
const path = require('path');
const nodemailer = require('nodemailer');
const XLSX = require('xlsx');
const moment = require('moment');
const axios = require('axios');

const app = express();

// Middleware setup
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(session({
    secret: 'your_secret_key',
    resave: false,
    saveUninitialized: true
}));

// View engine setup
app.set('view engine', 'ejs'); // Using EJS instead of Jinja2
app.set('views', path.join(__dirname, 'views'));

// MongoDB setup
const mongoUri = process.env.MONGODB_URI || 'mongodb+srv://ceo:m1jZaiWN2ulUH0ux@cluster1.zdfza.mongodb.net/';
let db, usersCollection, misCollection;

async function connectDB() {
    try {
        const client = await MongoClient.connect(mongoUri);
        db = client.db('test');
        usersCollection = db.collection('users');
        misCollection = db.collection('mis');
        console.log("MongoDB connection successful!");
    } catch (err) {
        console.error("MongoDB connection failed:", err);
    }
}
connectDB();

// Helper function to format date
function formatDate(dateStr) {
    const formats = [
        'YYYY-MM-DD HH:mm:ss',
        'YYYY-MM-DD',
        'MM/DD/YYYY',
        'DD-MM-YYYY',
        'DD/MM/YYYY',
        'YYYY/MM/DD'
    ];

    for (const format of formats) {
        const date = moment(dateStr, format, true);
        if (date.isValid()) {
            return date.format('DD-MM-YYYY');
        }
    }
    return null;
}

// Authentication middleware
function requireAuth(req, res, next) {
    if (req.session.username) {
        next();
    } else {
        res.redirect('/login');
    }
}

function requireFullAccess(req, res, next) {
    if (req.session.username && req.session.access_level === 'full') {
        next();
    } else {
        res.status(403).send("Unauthorized Access");
    }
}

// Routes
app.get('/', (req, res) => {
    res.render('login');
});

app.post('/login', (req, res) => {
    const { username, password } = req.body;
    req.session.username = username;

    if (password === '123123') {
        req.session.access_level = 'limited';
        res.redirect('/home');
    } else if (password === '123456') {
        req.session.access_level = 'full';
        res.redirect('/home');
    } else {
        res.status(401).send("Invalid Credentials");
    }
});

app.get('/home', requireAuth, (req, res) => {
    res.render('home', {
        username: req.session.username,
        access_level: req.session.access_level
    });
});

// File upload configuration
const storage = multer.memoryStorage();
const upload = multer({ storage: storage });

app.post('/data_upload', requireAuth, upload.array('file'), async (req, res) => {
    try {
        if (!req.files || req.files.length === 0) {
            return res.redirect('/data_upload');
        }

        const collection_type = req.body.collection_type;
        const lender_name = req.body.lender;
        const collection = collection_type === 'mis' ? misCollection : usersCollection;

        for (const file of req.files) {
            // Process each file based on type
            let data;
            if (file.originalname.endsWith('.csv')) {
                // Process CSV
                const workbook = XLSX.read(file.buffer);
                data = XLSX.utils.sheet_to_json(workbook.Sheets[workbook.SheetNames[0]]);
            } else if (file.originalname.endsWith('.xlsx')) {
                // Process Excel
                const workbook = XLSX.read(file.buffer);
                data = XLSX.utils.sheet_to_json(workbook.Sheets[workbook.SheetNames[0]]);
            }

            // Process data based on lender
            if (data) {
                const processedData = processLenderData(data, lender_name);
                await saveToMongoDB(processedData, collection);
            }
        }

        res.redirect('/data_upload');
    } catch (error) {
        console.error('Upload error:', error);
        res.redirect('/data_upload');
    }
});

// Helper function to process lender data
function processLenderData(data, lenderName) {
    // Implementation of lender-specific data processing
    // This would contain the logic from the Python version for each lender
    // Return processed data
}

// Helper function to save to MongoDB
async function saveToMongoDB(data, collection) {
    // Implementation of MongoDB save logic
    // This would contain the bulk write operations
}

// Additional routes would follow...

// Start server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
}); 