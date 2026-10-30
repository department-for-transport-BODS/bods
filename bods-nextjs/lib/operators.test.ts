import { formatOperatorDate, operatorLicenceUrl, operatorPublishUrl, truncateChars, djangoValue } from './operators';
import { dataPath, publishPath } from '@/config/client';

describe('operator helpers', () => {
  it('truncates like Django truncatechars (length includes the ellipsis)', () => {
    expect(truncateChars('Short', 19)).toBe('Short');
    expect(truncateChars('1234567890123456789', 19)).toBe('1234567890123456789');
    expect(truncateChars('12345678901234567890', 19)).toBe('123456789012345678…');
  });

  it('formats dates like Django "j F Y" in London time', () => {
    expect(formatOperatorDate('2023-03-05T10:00:00Z')).toBe('5 March 2023');
    // 23:30 UTC in summer is 00:30 the next day in London
    expect(formatOperatorDate('2024-06-30T23:30:00Z')).toBe('1 July 2024');
  });

  it('renders null like a Django template', () => {
    expect(djangoValue(null)).toBe('None');
    expect(djangoValue(0)).toBe('0');
  });

  it('builds Django-matching licence and publish URLs', () => {
    expect(operatorLicenceUrl('PD0001', 3)).toBe(dataPath('/operators/licence/PD0001/?org_id=3'));
    expect(operatorPublishUrl(3, 'compliance-report')).toBe(
      publishPath('/org/3/dataset/timetable/compliance-report/'),
    );
    expect(operatorPublishUrl(3, 'service-codes')).toBe(publishPath('/org/3/dataset/timetable/service-codes/'));
    expect(operatorPublishUrl(3, 'ppc-archive')).toBe(publishPath('/org/3/dataset/ppc-archive/'));
    expect(operatorPublishUrl(3, 'data-activity')).toBe(
      publishPath('/org/3/dataset/data-activity/?prev=operator-detail'),
    );
  });
});
