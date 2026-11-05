import { defineCollection, z } from 'astro:content'
import { glob } from 'astro/loaders'

const prose = z.object({
  title: z.string(),
  description: z.string().optional(),
})

// Keep `mechanical/index.md` → id `mechanical/index` so legacy URLs (/competitions/mechanical/index.html)
// stay distinct from /competitions/mechanical.html. Astro's default slug drops the trailing `index`.
const generateId = ({ entry }: { entry: string }) => entry.replace(/\.md$/, '')

const learn = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/learn', generateId }),
  schema: prose,
})

const competitions = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/competitions', generateId }),
  schema: prose,
})

const notice = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/notice', generateId }),
  schema: prose,
})

export const collections = { learn, competitions, notice }
