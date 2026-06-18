import mongoose from 'mongoose';

const analysisSchema = new mongoose.Schema({
  sample_id: { type: mongoose.Schema.Types.ObjectId, ref: 'Sample', required: true },
  type: { type: String, enum: ['hole', 'fracture', 'grain', 'mineral'], required: true },
  status: { type: String, enum: ['pending', 'processing', 'done', 'failed'], default: 'pending' },
  params: { type: Object, default: {} },
  results: { type: Object, default: {} },
  report_html: { type: String },
  confidence: { type: Number, min: 0, max: 1 },
  created_by: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
  created_at: { type: Date, default: Date.now }
});

export default mongoose.model('Analysis', analysisSchema);
