import { localAuthorityExportHandler } from '@/lib/local-authority-export-route';

const proxyExport = localAuthorityExportHandler('/local-authority/compliance-report/');

export const GET = proxyExport;
export const HEAD = proxyExport;
