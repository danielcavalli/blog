// A page of the site that is text alone (About, the CV): the post's measure, without contents or
// notes. A CV's sections open on a fine rule, as a record's do.

import { Reading, ReadingBody, ReadingHead } from "@mare-rio/design-system/react";

import { Tree } from "../reef/Tree";
import type { PlainModel } from "./models";

export function PlainBody({ page }: { page: PlainModel }) {
  return (
    <Reading>
      <ReadingHead facts={[page.fact]} title={page.title} dek={page.dek} />
      <ReadingBody sections={page.which === "cv" ? "ruled" : "titled"}>
        <Tree nodes={page.body} />
      </ReadingBody>
    </Reading>
  );
}
