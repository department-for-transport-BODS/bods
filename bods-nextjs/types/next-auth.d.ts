/**
 * NextAuth Type Extensions
 * 
 * Extend NextAuth types to include Django token and user roles
 */

import 'next-auth';
import type { User } from './index';

declare module 'next-auth' {
  interface Session {
    user: User & {
      id: string;
      roles?: string[];
      isStaff?: boolean;
      isSuperuser?: boolean;
    };
    djangoToken: string;
  }

  interface User {
    djangoToken?: string;
    roles?: string[];
    isStaff?: boolean;
    isSuperuser?: boolean;
  }
}

declare module 'next-auth/jwt' {
  interface JWT {
    djangoToken?: string;
    roles?: string[];
    isStaff?: boolean;
    isSuperuser?: boolean;
  }
}

