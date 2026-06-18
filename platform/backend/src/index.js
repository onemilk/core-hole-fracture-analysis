import express from 'express';
import cors from 'cors';
import { connectDB } from './models/db.js';

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

import authRoutes from './routes/auth.js';
import sampleRoutes from './routes/samples.js';
import analysisRoutes from './routes/analysis.js';

app.use('/api/auth', authRoutes);
app.use('/api/samples', sampleRoutes);
app.use('/api/analysis', analysisRoutes);

app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

connectDB().then(() => {
  app.listen(PORT, () => {
    console.log(`Backend listening on port ${PORT}`);
  });
});
