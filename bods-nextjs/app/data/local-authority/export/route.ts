import { localAuthorityExportHandler } from '@/lib/local-authority-export-route';

const proxyExport = localAuthorityExportHandler('/local-authority/export/');

export const GET = proxyExport;
export const HEAD = proxyExport;
