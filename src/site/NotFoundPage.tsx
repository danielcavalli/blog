// The page for an address that is not there: it says so, and where everything is.

import { Empty, Link, Reading } from "@mare-rio/design-system/react";

import { WORDS, type Lang } from "./words";

export function MissingBody({ lang }: { lang: Lang }) {
  const words = WORDS[lang];
  return (
    <Reading>
      <Empty title={words.missing.title}>
        {words.missing.help} <Link href={`/${lang}/blog/`}>{words.landing.blog}</Link>
      </Empty>
    </Reading>
  );
}
