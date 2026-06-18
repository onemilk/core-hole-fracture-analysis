import { Router } from 'express';
import multer from 'multer';
import path from 'path';
import { authMiddleware, roleMiddleware } from '../middleware/auth.js';
import Sample from '../models/Sample.js';

const router = Router();
router.use(authMiddleware);

const upload = multer({
  dest: path.join(process.cwd(), 'uploads'),
  limits: { fileSize: 50 * 1024 * 1024 },
  fileFilter: (req, file, cb) => {
    const allowed = ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp'];
    const ext = path.extname(file.originalname).toLowerCase();
    cb(null, allowed.includes(ext));
  }
});

router.get('/', async (req, res) => {
  const samples = await Sample.find().limit(20);
  res.json(samples);
});

router.post('/', authMiddleware, roleMiddleware('admin', 'teacher'), async (req, res) => {
  try {
    const sample = await Sample.create({ ...req.body, created_by: req.user.id });
    res.status(201).json(sample);
  } catch (e) {
    res.status(400).json({ error: e.message });
  }
});

router.post('/:id/images', upload.single('image'), async (req, res) => {
  try {
    const sample = await Sample.findById(req.params.id);
    if (!sample) return res.status(404).json({ error: 'Sample not found' });
    sample.image_files.push({
      filename: req.file.originalname,
      path: req.file.path,
      mimetype: req.file.mimetype,
      size: req.file.size
    });
    await sample.save();
    res.json(sample);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

router.delete('/:id', authMiddleware, roleMiddleware('admin'), async (req, res) => {
  try {
    await Sample.findByIdAndDelete(req.params.id);
    res.json({ message: 'Deleted' });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

export default router;
