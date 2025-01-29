const express = require('express');
const router = express.Router();

// Define routes
router.get('/', (req, res) => {
    res.render('login');
});

// Export router
module.exports = router; 