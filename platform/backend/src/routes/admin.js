import { Router } from 'express';
import { authMiddleware, roleMiddleware } from '../middleware/auth.js';
import User from '../models/User.js';

const router = Router();

router.use(authMiddleware, roleMiddleware('admin'));

router.get('/users', async (req, res) => {
  const users = await User.find().select('-password_hash');
  res.json(users);
});

router.put('/users/:id/role', async (req, res) => {
  const { role } = req.body;
  if (!['admin', 'teacher', 'student'].includes(role)) {
    return res.status(400).json({ error: 'Invalid role' });
  }
  const user = await User.findByIdAndUpdate(req.params.id, { role }, { new: true })
    .select('-password_hash');
  if (!user) return res.status(404).json({ error: 'User not found' });
  res.json(user);
});

router.delete('/users/:id', async (req, res) => {
  await User.findByIdAndDelete(req.params.id);
  res.json({ message: 'User deleted' });
});

export default router;
