import { Router } from 'express';
import { authMiddleware } from '../middleware/auth.js';
import Analysis from '../models/Analysis.js';
import { runAnalysis } from '../services/engine.js';

const router = Router();
router.use(authMiddleware);

router.post('/', async (req, res) => {
  try {
    const { sample_id, type, image_path, params } = req.body;
    const analysis = await Analysis.create({
      sample_id, type, params, status: 'pending', created_by: req.user.id
    });

    runAnalysis(image_path, type, params)
      .then(async (result) => {
        analysis.status = 'done';
        analysis.results = result;
        await analysis.save();
      })
      .catch(async (err) => {
        analysis.status = 'failed';
        analysis.results = { error: err.message };
        await analysis.save();
      });

    res.status(202).json({ task_id: analysis._id, status: 'pending' });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

router.get('/:id', async (req, res) => {
  const analysis = await Analysis.findById(req.params.id).populate('sample_id');
  if (!analysis) return res.status(404).json({ error: 'Analysis not found' });
  res.json(analysis);
});

router.get('/sample/:sampleId', async (req, res) => {
  const analyses = await Analysis.find({ sample_id: req.params.sampleId })
    .sort({ created_at: -1 }).limit(20);
  res.json(analyses);
});

export default router;
