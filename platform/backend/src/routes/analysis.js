import { Router } from 'express';
import { authMiddleware } from '../middleware/auth.js';
import Analysis from '../models/Analysis.js';

const router = Router();
router.use(authMiddleware);

router.get('/', async (req, res) => {
  const analyses = await Analysis.find().limit(20);
  res.json(analyses);
});

export default router;
