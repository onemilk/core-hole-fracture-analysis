import { Router } from 'express';
import { authMiddleware } from '../middleware/auth.js';
import Sample from '../models/Sample.js';

const router = Router();
router.use(authMiddleware);

router.get('/', async (req, res) => {
  const samples = await Sample.find().limit(20);
  res.json(samples);
});

export default router;
