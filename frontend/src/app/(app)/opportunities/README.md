# Why this segment has no `loading.tsx`

A `loading.tsx` here would create a Suspense boundary covering the child route
`[slug]` as well, which caused two defects:

1. Opening an opportunity detail page showed the *feed's* card-grid skeleton.
2. Streaming flushed a `200` before the page resolved, so `notFound()` for a
   missing opportunity could only swap the UI — the status stayed `200`.

Instead, the feed page streams its own results with `<Suspense>` around the
`Results` component, so the header and filters paint immediately while the grid
loads. The detail route deliberately has no loading file: it is a single fetch,
and a correct `404` matters more than a skeleton.
