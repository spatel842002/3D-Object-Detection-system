# Component View

```mermaid
graph TD
    subgraph API Process
        App[FastAPI app.py]
        Deps[api/deps.py\nlru_cache singletons]
        Pipe[pipeline.DetectionPipeline]
        Det[detection.YoloDetector]
        Depth[depth.MidasDepthEstimator]
        Calib[calibration.py]
        Track[tracking.IouTracker]
        Jobs[jobs.JobStore]
        Store[storage.ObjectStorage]
        Cfg[config.Settings]
    end

    App --> Deps
    Deps --> Pipe
    Deps --> Store
    Deps --> Jobs
    Pipe --> Det
    Pipe --> Depth
    Pipe --> Calib
    App --> Track
    App --> Cfg
    Cfg -. env vars .-> App
```

Each box under "API Process" is a Python module with a narrow interface
(`Detector`, `DepthEstimator`, `ObjectStorage` are `typing.Protocol`s), so
production adapters (S3 vs. local filesystem) and test doubles (fake
detector/depth estimator) are interchangeable without touching
`pipeline.py` or `app.py`. See `tests/conftest.py` for the fakes and
`tests/contract/test_api.py` for how they're wired into the FastAPI app
via `dependency_overrides`.
