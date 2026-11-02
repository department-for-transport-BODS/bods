import { timetableFeedStatusIndicator } from './timetableFeedStatus';

describe('timetableFeedStatusIndicator', () => {
  it.each([
    ['live', 'Published', 'status-indicator--success'],
    ['indexing', 'Processing', 'status-indicator--indexing'],
    ['pending', 'Processing', 'status-indicator--indexing'],
    ['warning', 'Warning', 'status-indicator--warning'],
    ['expiring', 'Soon to expire', 'status-indicator--warning'],
    ['error', 'Error', 'status-indicator--error'],
    ['draft', 'Draft', 'status-indicator--draft'],
    ['success', 'Draft', 'status-indicator--draft'],
    ['expired', 'Expired', 'status-indicator--inactive'],
    ['inactive', 'Inactive', 'status-indicator--inactive'],
    ['deleted', 'Deleted', 'status-indicator--error'],
  ])('maps %s to %s', (status, label, className) => {
    expect(timetableFeedStatusIndicator(status)).toEqual({ label, className });
  });

  it('falls back to the raw status text', () => {
    expect(timetableFeedStatusIndicator('mystery')).toEqual({ label: 'mystery', className: '' });
  });
});
