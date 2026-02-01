/**
 * MSW Server Configuration
 * Erstellt Mock Server für Tests
 */

import { setupServer } from 'msw/node';
import { handlers } from './handlers';

// Erstelle Server mit Standard-Handlers
export const server = setupServer(...handlers);
