/**
 * Stable-ID helpers. Client-safe: no corpus import, so this may be used from a component.
 *
 * Every corpus record is addressed by a prefixed stable id ("vocab:1580640", "kanji:食",
 * "les:n5-saudacoes-01"). Routes carry the part after the prefix, because the prefix is already
 * implied by the route itself.
 */

/** "vocab:1580640" -> "1580640". A value with no prefix is returned unchanged. */
export function idPart(ref: string): string {
  const i = ref.indexOf(":");
  return i === -1 ? ref : ref.slice(i + 1);
}

/**
 * Link to a vocabulary entry.
 *
 * Takes the record's `slug`, never its headword: 93 headwords are shared by 193 records, so
 * /vocabulario/人 cannot say whether it means the N5 "pessoa" or the N1 sense.
 */
export function vocabHref(slug: string): string {
  return `/vocabulario/${encodeURIComponent(idPart(slug))}`;
}
