const { put } = require('@vercel/blob');

module.exports = async function handler(req, res) {
  if (req.method === 'OPTIONS') {
    res.status(204).end();
    return;
  }
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  const { page, description, contact } = req.body || {};
  if (!description || description.trim().length < 10) {
    res.status(400).json({ error: 'Description must be at least 10 characters' });
    return;
  }
  if (description.length > 2000) {
    res.status(400).json({ error: 'Description too long (max 2000 characters)' });
    return;
  }

  const entry = {
    page: (page || 'general').slice(0, 100),
    description: description.trim().slice(0, 2000),
    contact: contact ? contact.trim().slice(0, 100) : null,
    timestamp: new Date().toISOString(),
  };

  const key = `feedback/${Date.now()}-${Math.random().toString(36).slice(2, 8)}.json`;

  try {
    await put(key, JSON.stringify(entry, null, 2), {
      access: 'public',
      contentType: 'application/json',
    });
    console.log('Feedback stored:', key, JSON.stringify(entry));
    res.status(200).json({ ok: true });
  } catch (err) {
    console.error('Feedback storage failed:', err.message);
    console.log('Feedback (log fallback):', JSON.stringify(entry));
    res.status(200).json({ ok: true, note: 'logged' });
  }
};
