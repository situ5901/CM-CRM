const express = require('express');
const router = express.Router();

router.get('/', requireFullAccess, async (req, res) => {
    try {
        const data = await misCollection.find({}, {
            projection: {
                _id: 0,
                phone: 1,
                disbursedamount: 1,
                disbursaldate: 1,
                status: 1,
                Lender: 1,
                createdAt: 1,
                partner: 1
            }
        }).toArray();

        // Process data similar to Python version
        // Format dates, calculate totals, etc.

        res.render('dashboard', {
            username: req.session.username,
            table_data: data,
            total_disbursed,
            total_count,
            month_options,
            lender_options,
            created_at_options
        });
    } catch (error) {
        res.status(500).send("Error loading dashboard");
    }
});

module.exports = router; 