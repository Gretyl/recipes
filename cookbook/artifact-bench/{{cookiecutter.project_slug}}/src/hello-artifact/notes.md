# Notes — hello-artifact

Persistence is optional-chained (`store?.getItem`, `store?.setItem`)
because the artifact must run unmodified both inside Claude (where
`window.storage` exists) and in a vanilla browser opened from
`public/` (where it does not). Failing closed on storage absence
would defeat the "copy-pasteable HTML" property the proposal calls
out as the artifact contract.
