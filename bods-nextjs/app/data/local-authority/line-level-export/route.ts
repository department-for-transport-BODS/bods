import { localAuthorityExportHandler } from '@/lib/local-authority-export-route';

const proxyExport = localAuthorityExportHandler('/local-authority/line-level-export/');

export const GET = proxyExport;
export const HEAD = proxyExport;
