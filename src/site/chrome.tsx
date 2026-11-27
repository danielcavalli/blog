// What every page of the site but its landing stands between: the bar and the foot.

import { useEffect } from "react";

import { BarEnd, Foot, Languages, Link, Nav, NavItem, ThemeToggle, TopBar, Wordmark } from "@mare-rio/design-system/react";

import { WORDS, type Alternates, type Lang } from "./words";

/** The reader's other language: the same page there, or that language's front door. Each is a real link. */
export function LanguageChoice({ lang, alternates }: { lang: Lang; alternates: Alternates }) {
  const to = (code: Lang) => alternates[code] ?? `/${code}/`;
  // The language being read is remembered, so the site's root opens in it next time.
  useEffect(() => {
    try {
      window.localStorage.setItem("dan.rio-lang", lang);
    } catch {}
  }, [lang]);
  return (
    <Languages
      current={lang.toUpperCase()}
      choices={[
        { label: "EN", href: to("en"), hreflang: "en" },
        { label: "PT", href: to("pt"), hreflang: "pt-BR" },
      ]}
    />
  );
}

export function Bar({ lang, at, alternates }: { lang: Lang; at?: "blog" | "about" | "cv"; alternates: Alternates }) {
  const places = WORDS[lang].places;
  return (
    <TopBar>
      <Wordmark href={`/${lang}/`}>dan.rio</Wordmark>
      <Nav>
        <NavItem href={`/${lang}/blog/`} current={at === "blog"}>{places.blog}</NavItem>
        <NavItem href={`/${lang}/about`} current={at === "about"}>{places.about}</NavItem>
        <NavItem href={`/${lang}/cv`} current={at === "cv"}>{places.cv}</NavItem>
      </Nav>
      <BarEnd>
        <LanguageChoice lang={lang} alternates={alternates} />
        <ThemeToggle />
      </BarEnd>
    </TopBar>
  );
}

export function SiteFoot({ lang }: { lang: Lang }) {
  return (
    <Foot
      left={WORDS[lang].foot}
      right={
        <>
          <Link href="https://x.com/dancavlli">x</Link> <Link href="https://github.com/danielcavalli">github</Link>{" "}
          <Link href="https://www.linkedin.com/in/cavallidaniel/">linkedin</Link>
        </>
      }
    />
  );
}
