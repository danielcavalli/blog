// The page for an address that is not there: it says so, and where everything is.

import { useEffect, useState } from "react";

import { Empty, Link, Page, Reading } from "@mare-rio/design-system/react";

import { Bar, SiteFoot } from "./chrome";
import { WORDS, type Lang } from "./words";

export function NotFoundPage() {
  // One page answers for every missing address: it speaks the language of the address asked for.
  const [lang, setLang] = useState<Lang>("en");
  useEffect(() => {
    if (window.location.pathname.startsWith("/pt")) setLang("pt");
  }, []);
  const words = WORDS[lang];
  return (
    <Page variant="reading" box="folha">
      <Bar lang={lang} alternates={{ en: "/en/", pt: "/pt/" }} />
      <Reading>
        <Empty title={words.missing.title}>
          {words.missing.help} <Link href={`/${lang}/blog/`}>{words.landing.blog}</Link>
        </Empty>
      </Reading>
      <SiteFoot lang={lang} />
    </Page>
  );
}
