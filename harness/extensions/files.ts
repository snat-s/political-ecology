/** File tools confined to the workspace. */
import {constants} from 'node:fs';
import {open, readdir, realpath} from 'node:fs/promises';
import {basename, dirname, isAbsolute, relative, resolve} from 'node:path';
import type {ExtensionAPI} from '@earendil-works/pi-coding-agent';
import {Type} from 'typebox';
import {requiredEnvironment} from './ledger.ts';

function isContained(root: string, candidate: string): boolean {
  const relation = relative(root, candidate);
  return (
    relation === '' || (!relation.startsWith('..') && !isAbsolute(relation))
  );
}

async function workspaceRoot(): Promise<string> {
  return realpath(requiredEnvironment('POLITICAL_ECOLOGY_WORKSPACE'));
}

async function readablePath(requested: string): Promise<string> {
  const root = await workspaceRoot();
  const candidate = await realpath(resolve(root, requested));
  if (!isContained(root, candidate))
    throw new Error('path is outside the workspace');
  return candidate;
}

async function writablePath(requested: string): Promise<string> {
  const root = await workspaceRoot();
  const lexical = resolve(root, requested);
  if (!isContained(root, lexical))
    throw new Error('path is outside the workspace');
  // Requiring an existing canonical parent prevents `..` and directory-symlink
  // escapes. O_NOFOLLOW below separately rejects a final-component symlink.
  const parent = await realpath(dirname(lexical));
  if (!isContained(root, parent))
    throw new Error('path is outside the workspace');
  return resolve(parent, basename(lexical));
}

export function registerFileTools(pi: ExtensionAPI) {
  pi.registerTool({
    name: 'ls',
    label: 'List directory',
    description:
      'List names in a workspace directory. path defaults to ".", the main workspace directory. Directory names end with "/".',
    parameters: Type.Object(
      {path: Type.Optional(Type.String({minLength: 1}))},
      {additionalProperties: false},
    ),
    async execute(_toolCallId, params) {
      try {
        const path = await readablePath(params.path ?? '.');
        const entries = await readdir(path, {withFileTypes: true});
        const names = entries
          .map(entry => entry.name + (entry.isDirectory() ? '/' : ''))
          .sort();
        return {
          content: [{type: 'text', text: JSON.stringify(names)}],
          details: {path, count: names.length},
        };
      } catch (error) {
        return {
          content: [{type: 'text', text: (error as Error).message}],
          details: {},
          isError: true,
        };
      }
    },
  });

  pi.registerTool({
    name: 'read',
    label: 'Read',
    description:
      'Read part of a UTF-8 text file in the workspace. offset is a character position; a negative offset reads from the end. limit sets the maximum number of characters to read.',
    parameters: Type.Object(
      {
        path: Type.String({minLength: 1}),
        offset: Type.Optional(Type.Integer()),
        limit: Type.Optional(Type.Integer({minimum: 1, maximum: 20000})),
      },
      {additionalProperties: false},
    ),
    async execute(_toolCallId, params) {
      try {
        const path = await readablePath(params.path);
        const handle = await open(
          path,
          constants.O_RDONLY | constants.O_NOFOLLOW,
        );
        try {
          const text = await handle.readFile({encoding: 'utf8'});
          const totalLength = text.length;
          const requestedOffset = params.offset ?? 0;
          const offset = Math.min(
            totalLength,
            requestedOffset < 0
              ? Math.max(0, totalLength + requestedOffset)
              : requestedOffset,
          );
          const defaultLimit = totalLength || 1;
          const limit = params.limit ?? defaultLimit;
          const end = Math.min(totalLength, offset + limit);
          return {
            content: [{type: 'text', text: text.slice(offset, end)}],
            details: {
              path,
              offset,
              end,
              totalLength,
              hasMore: end < totalLength,
            },
          };
        } finally {
          await handle.close();
        }
      } catch (error) {
        return {
          content: [{type: 'text', text: (error as Error).message}],
          details: {},
          isError: true,
        };
      }
    },
  });

  pi.registerTool({
    name: 'write',
    label: 'Write',
    description: 'Write a UTF-8 text file in the workspace.',
    parameters: Type.Object(
      {path: Type.String({minLength: 1}), content: Type.String()},
      {additionalProperties: false},
    ),
    async execute(_toolCallId, params) {
      try {
        const path = await writablePath(params.path);
        const handle = await open(
          path,
          constants.O_WRONLY |
            constants.O_CREAT |
            constants.O_NOFOLLOW |
            constants.O_TRUNC,
          0o644,
        );
        try {
          await handle.writeFile(params.content, {encoding: 'utf8'});
        } finally {
          await handle.close();
        }
        return {
          content: [
            {
              type: 'text',
              text: `Wrote ${Buffer.byteLength(params.content)} bytes.`,
            },
          ],
          details: {path},
        };
      } catch (error) {
        return {
          content: [{type: 'text', text: (error as Error).message}],
          details: {},
          isError: true,
        };
      }
    },
  });
}
