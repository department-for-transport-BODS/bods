import { CoachDownloadContent } from './_components/CoachDownloadContent';

export const metadata = {
  title: { absolute: 'All coach data' },
  description: 'Download all coach data published on the Bus Open Data Service.',
};

// Public in Django (CoachDownloadView has no login requirement).
export default function CoachDownloadPage() {
  return <CoachDownloadContent />;
}
