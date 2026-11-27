// The site's threshold: its name written in paint and alive, who writes here, the three places, and
// the sea at the floor of the screen.

import { BarEnd, Foot, HorizonMark, Nav, NavItem, Page, ThemeToggle, Threshold, TopBar, Voice, Wordmark } from "@mare-rio/design-system/react";

import { LanguageChoice } from "./chrome";
import type { LandingModel } from "./models";
import { WORDS } from "./words";

export function LandingPage({ landing }: { landing: LandingModel }) {
  const { lang } = landing;
  const words = WORDS[lang];
  return (
    <Page variant="shore">
      <TopBar>
        <BarEnd>
          <LanguageChoice lang={lang} alternates={landing.alternates} />
          <ThemeToggle />
        </BarEnd>
      </TopBar>
      <Threshold>
        <Wordmark size="display" href={`/${lang}/`}>dan.rio</Wordmark>
        <Voice>{words.landing.voice}</Voice>
        <Nav>
          <NavItem href={`/${lang}/blog/`}>{words.landing.blog}</NavItem>
          <NavItem href={`/${lang}/about`}>{words.landing.about}</NavItem>
          <NavItem href={`/${lang}/cv`}>{words.landing.cv}</NavItem>
        </Nav>
      </Threshold>
      <HorizonMark />
      <Foot left={`${words.posts(landing.count)} · ${words.landing.latest} ${landing.latest.toLowerCase()}`} right="dan.rio" />
    </Page>
  );
}
