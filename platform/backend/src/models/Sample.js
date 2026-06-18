import mongoose from 'mongoose';

const sampleSchema = new mongoose.Schema({
  sample_id: { type: String, required: true, unique: true },
  basin: { type: String, required: true },
  well_id: { type: String, required: true },
  top_depth: { type: Number, required: true },
  bottom_depth: { type: Number, required: true },
  lithology: { type: Object, default: {} },
  resolution_dpi: { type: Number, enum: [600, 1200], default: 600 },
  image_files: [{ type: mongoose.Schema.Types.ObjectId, ref: 'ImageFile' }],
  created_by: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
  created_at: { type: Date, default: Date.now }
});

sampleSchema.index({ basin: 1, well_id: 1 });

export default mongoose.model('Sample', sampleSchema);
