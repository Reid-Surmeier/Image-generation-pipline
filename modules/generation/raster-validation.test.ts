import assert from "node:assert/strict"
import { createHash } from "node:crypto"
import test from "node:test"
import { Effect } from "effect"
import { ApplicationFiles, MediaInspector, PlanningIdentity, byteMediaInspector, plan } from "../conductor/index.js"
import { prepare, validatePersisted, type GenerationResult } from "./index.js"
import { makeFixture } from "../../tests/control-plane-fixture.js"

// Issue #103: exercise the public evidence validator with production-sized pixels.
test("validates canonical megapixel evidence efficiently and rejects malformed rasters", async () => {
  const fixture = makeFixture("qwen-image")
  const decision = await Effect.runPromise(plan({ objectivePath: fixture.objectivePath }).pipe(
    Effect.provideService(ApplicationFiles, fixture.files),
    Effect.provideService(MediaInspector, byteMediaInspector),
    Effect.provideService(PlanningIdentity, fixture.identity),
  ))
  assert.equal(decision._tag, "Planned")
  if (decision._tag !== "Planned") return
  const ref = decision.run.request.references[0]!
  const prepared = await Effect.runPromise(prepare(decision.run.request, [{ ...ref, bytes: (await Effect.runPromise(fixture.files.read(ref.applicationPath))).bytes }]))
  const hash = (body: Uint8Array) => createHash("sha256").update(body).digest("hex")
  const receipt = Buffer.from('{"id":"offline-raster","status":"completed"}')
  const result = (source: string): GenerationResult => {
    const body = Buffer.from(source)
    return { provider: "openrouter", model: prepared.request.model,
      providerEvidence: { mediaType: "application/json", body: receipt, sha256: hash(receipt) },
      outputs: [{ applicationPath: "outputs/raster.rgba.json", mediaType: "application/vnd.qwen.rgba+json", body, sha256: hash(body) }] }
  }
  const source = JSON.stringify({ height: 1024, pixels: Array(1024 * 1024 * 4).fill(128), width: 1024 })
  const started = performance.now()
  await Effect.runPromise(validatePersisted(prepared, result(source)))
  const elapsed = Math.round(performance.now() - started)
  console.log(JSON.stringify({ rasterValidationMs: elapsed, bytes: source.length }))
  assert(elapsed < 1500, `Canonical raster validation took ${elapsed}ms (budget 1500ms)`)
  for (const malformed of [
    '{"height":1,"height":1,"pixels":[0,0,0,255],"width":1}',
    '{"width":1,"height":1,"pixels":[0,0,0,255]}',
    '{"height":1,"pixels":[0,0,0,256],"width":1}',
    '{"height":0,"pixels":[],"width":1}',
    '{"extra":0,"height":1,"pixels":[0,0,0,255],"width":1}',
  ]) assert.equal((await Effect.runPromise(Effect.flip(validatePersisted(prepared, result(malformed))))).code, "ADAPTER_RESULT_INVALID")
})
