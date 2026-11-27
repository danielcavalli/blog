// A page of the site that is text alone (About, the CV): the post's measure, without contents or
// notes. A CV's sections open on a fine rule, as a record's do.

import { Page, Reading, ReadingBody, ReadingHead } from "@mare-rio/design-system/react";

import { Tree } from "../reef/Tree";
import { Bar, SiteFoot } from "./chrome";
import type { PlainModel } from "./models";

export function PlainPage({ page }: { page: PlainModel }) {
  return (
    <Page variant="reading">
      <Bar lang={page.lang} at={page.which} alternates={page.alternates} />
      <Reading>
        <ReadingHead facts={[page.fact]} title={page.title} dek={page.dek} />
        <ReadingBody sections={page.which === "cv" ? "ruled" : "titled"}>
          <Tree nodes={page.body} />
        </ReadingBody>
      </Reading>
      <SiteFoot lang={page.lang} />
    </Page>
  );
}
