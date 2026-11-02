const { list } = require('@vercel/blob');

module.exports = async function handler(req, res) {
  if (req.method !== 'GET') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  const key = req.query.key;
  if (!key || key !== process.env.FEEDBACK_KEY) {
    res.status(403).json({ error: 'Forbidden' });
    return;
  }

  try {
    const { blobs } = await list({ prefix: 'feedback/' });

    const entries = await Promise.all(
      blobs.map(async (blob) => {
        try {
          const resp = await fetch(blob.url);
          const data = await resp.json();
          return { ...data, _blobUrl: blob.url };
        } catch {
          return { _blobUrl: blob.url, _error: 'Failed to read' };
        }
      })
    );

    entries.sort((a, b) => {
      const ta = a.timestamp || '';
      const tb = b.timestamp || '';
      return tb.localeCompare(ta);
    });

    res.status(200).json({ count: entries.length, entries });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
};
