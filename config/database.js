const { MongoClient } = require('mongodb');

const mongoUri = process.env.MONGODB_URI || 'mongodb+srv://ceo:m1jZaiWN2ulUH0ux@cluster1.zdfza.mongodb.net/';

let db = null;

async function connectDB() {
    try {
        const client = await MongoClient.connect(mongoUri);
        db = client.db('test');
        console.log("MongoDB connection successful!");
        return db;
    } catch (err) {
        console.error("MongoDB connection failed:", err);
        throw err;
    }
}

function getDB() {
    return db;
}

module.exports = {
    connectDB,
    getDB
}; 