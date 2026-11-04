import type { Metadata } from 'next';
import SelectOrgContent from './_components/SelectOrgContent';

export const metadata: Metadata = {
  title: 'Operator Dashboard',
};

export default function SelectOrgPage() {
  return <SelectOrgContent />;
}
