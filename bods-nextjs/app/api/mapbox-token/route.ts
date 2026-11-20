import { NextResponse } from 'next/server';
import { serverConfig } from '@/config/server';

export function GET() {
  return NextResponse.json({ token: serverConfig.mapboxToken });
}