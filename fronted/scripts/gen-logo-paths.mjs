import { readFileSync } from 'fs'
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'
import opentype from 'opentype.js'

const __dirname = dirname(fileURLToPath(import.meta.url))

const fontPath = resolve(__dirname, '../node_modules/@fontsource/nunito/files/nunito-latin-900-normal.woff')
const buffer   = readFileSync(fontPath)
const font     = opentype.parse(buffer.buffer)

const SIZE    = 90
const START_X = 18
const Y       = 100

const letters = ['m', 'o', 'n', 'i']
let x = START_X
const results = []

for (const ch of letters) {
  const path = font.getPath(ch, x, Y, SIZE)
  const d    = path.toPathData(4)
  const adv  = font.getAdvanceWidth(ch, SIZE)
  results.push({ letter: ch, d, x: Math.round(x * 10) / 10, advance: Math.round(adv * 10) / 10 })
  x += adv
}

console.log('=== LETTER PATHS ===')
results.forEach(r => {
  process.stdout.write(`\nLETTER_${r.letter.toUpperCase()}: x=${r.x} adv=${r.advance}\n`)
  process.stdout.write(r.d + '\n')
})

const totalW = x - START_X
process.stdout.write(`\nTotal width: ${Math.round(totalW)}  viewBox: "0 0 ${Math.round(x + 18)} 115"\n`)
