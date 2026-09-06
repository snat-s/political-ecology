/** The only explicitly loaded Pi extension: guards, accounting, and five tools. */
import type {ExtensionAPI} from '@earendil-works/pi-coding-agent';
import {registerBudgetAccounting} from './budget.ts';
import {registerFileTools} from './files.ts';
import {registerTokenTools} from './ledger.ts';

const ALLOWED_TOOLS = new Set([
  'ls',
  'read',
  'write',
  'count_tokens',
  'get_tokens',
]);

export default function tokenEconomy(pi: ExtensionAPI) {
  // Defense in depth: even if launch flags regress, expose and execute only the
  // five experiment tools. In particular, never permit Pi's bash/edit tools.
  pi.on('session_start', () => {
    pi.setActiveTools(
      process.env.POLITICAL_ECOLOGY_FINAL_MESSAGE === '1'
        ? []
        : [...ALLOWED_TOOLS],
    );
  });
  pi.on('tool_call', event => {
    if (process.env.POLITICAL_ECOLOGY_FINAL_MESSAGE === '1') {
      return {
        block: true,
        reason: 'All tools are disabled during the final reflection',
      };
    }
    if (!ALLOWED_TOOLS.has(event.toolName)) {
      return {
        block: true,
        reason: `Tool ${event.toolName} is disabled by the experiment`,
      };
    }
  });

  registerBudgetAccounting(pi);
  registerFileTools(pi);
  registerTokenTools(pi);
}
