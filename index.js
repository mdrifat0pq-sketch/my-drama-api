const express = require('express');
const { MOVIES } = require('@consumet/extensions');
const app = express();
const port = process.env.PORT || 3000;

const dramaCloud = new MOVIES.DramaCool();

// হোম রুট
app.get('/', (req, res) => {
    res.send('My Drama API is Running!');
});

// ড্রামা সার্চ করার এন্ডপয়েন্ট
app.get('/search/:query', async (req, res) => {
    try {
        const query = req.params.query;
        const results = await dramaCloud.search(query);
        res.json(results);
    } catch (err) {
        res.status(500).json({ error: "Search failed", message: err.message });
    }
});

// ড্রামার এপিসোড এবং লিঙ্ক পাওয়ার এন্ডপয়েন্ট
app.get('/info/:id', async (req, res) => {
    try {
        const id = req.params.id;
        const info = await dramaCloud.fetchMediaInfo(id);
        res.json(info);
    } catch (err) {
        res.status(500).json({ error: "Fetching info failed" });
    }
});

// স্ট্রিমিং লিঙ্ক পাওয়ার এন্ডপয়েন্ট
app.get('/watch', async (req, res) => {
    try {
        const episodeId = req.query.episodeId;
        const mediaId = req.query.mediaId;
        const links = await dramaCloud.fetchEpisodeSources(episodeId, mediaId);
        res.json(links);
    } catch (err) {
        res.status(500).json({ error: "Streaming link not found" });
    }
});

app.listen(port, () => {
    console.log(`Server started on port ${port}`);
});
