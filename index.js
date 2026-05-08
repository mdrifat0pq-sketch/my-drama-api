const express = require('express');
const cors = require('cors'); // CORS লাইব্রেরি যোগ করা হয়েছে
const { MOVIES } = require('@consumet/extensions');

const app = express();
const port = process.env.PORT || 3000;

// CORS এনাবল করা হয়েছে যাতে আপনার HTML সাইট এপিআই ব্যবহার করতে পারে
app.use(cors());

const dramaCloud = new MOVIES.DramaCool();

// হোম পেজ চেক করার জন্য
app.get('/', (req, res) => {
    res.send('<h1>My Drama API is Running!</h1><p>Use /search/name to find dramas.</p>');
});

// সার্চ এন্ডপয়েন্ট
app.get('/search/:query', async (req, res) => {
    try {
        const query = req.params.query;
        const results = await dramaCloud.search(query);
        res.json(results);
    } catch (err) {
        res.status(500).json({ error: "Search failed", message: err.message });
    }
});

// ড্রামা ইনফো এন্ডপয়েন্ট
app.get('/info/:id', async (err, req, res) => {
    try {
        const id = req.params.id;
        const info = await dramaCloud.fetchMediaInfo(id);
        res.json(info);
    } catch (err) {
        res.status(500).json({ error: "Fetching info failed" });
    }
});

app.listen(port, () => {
    console.log(`Server is active on port ${port}`);
});
