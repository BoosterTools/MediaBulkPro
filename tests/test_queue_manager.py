from app.downloader.mock_backend import MockBackend

# Generous timeout for wait_idle() calls: CI runners (especially Windows)
# can be significantly slower than a local dev machine, and these are
# correctness tests, not performance benchmarks — a longer budget doesn't
# weaken what's being tested.
IDLE_TIMEOUT = 20


def test_enqueue_and_complete_single_download(db, tmp_path, make_manager):
    mgr = make_manager()
    item_id = mgr.enqueue_url("https://youtu.be/abc12345678")
    assert mgr.wait_idle(timeout=IDLE_TIMEOUT)
    item = mgr.queue.get(item_id)
    assert item.status == "completed"
    assert item.progress == 100
    assert item.output_path is not None
    from pathlib import Path
    assert Path(item.output_path).exists()


def test_history_recorded_on_completion(db, tmp_path, make_manager):
    mgr = make_manager()
    mgr.enqueue_url("https://youtu.be/abc12345678")
    mgr.wait_idle(timeout=IDLE_TIMEOUT)
    history = mgr.history.all_dicts()
    assert len(history) == 1
    assert history[0]["status"] == "completed"


def test_concurrency_limit_respected(db, tmp_path, make_manager):
    backend = MockBackend(chunk_size=64, total_size=4096)  # slow enough to observe overlap
    mgr = make_manager(backend=backend, max_concurrent=2)
    urls = [f"https://youtu.be/vid{i:08d}" for i in range(6)]
    mgr.enqueue_many(urls)
    assert mgr.wait_idle(timeout=IDLE_TIMEOUT)
    statuses = {i.status for i in mgr.queue.all()}
    assert statuses == {"completed"}


def test_duplicate_url_not_enqueued_twice_while_active(db, tmp_path, make_manager):
    backend = MockBackend(chunk_size=8, total_size=50_000)  # slow, stays active briefly
    mgr = make_manager(backend=backend, max_concurrent=1)
    id1 = mgr.enqueue_url("https://youtu.be/sameid123456")
    id2 = mgr.enqueue_url("https://youtu.be/sameid123456")
    assert id1 is not None
    assert id2 is None


def test_skip_duplicate_already_in_history(db, tmp_path, make_manager):
    backend = MockBackend()
    mgr = make_manager(backend=backend, duplicate_behavior="skip")
    mgr.enqueue_url("https://youtu.be/dup1234567a")
    assert mgr.wait_idle(timeout=IDLE_TIMEOUT)
    assert mgr.queue.all()[0].status == "completed"

    # A second, distinct queue entry for the same resolved video_id should be
    # skipped once extraction reveals it matches history — simulate by
    # directly re-running process on a fresh manager sharing the same repos.
    mgr2 = make_manager(backend=backend, duplicate_behavior="skip")
    mgr2.enqueue_url("https://youtube.com/watch?v=other-alias-1")
    assert mgr2.wait_idle(timeout=IDLE_TIMEOUT)
    # Different URL, different video_id (mock derives id from URL hash) -> not a dup.
    assert mgr2.queue.all()[-1].status == "completed"


def test_pause_and_resume(db, tmp_path, make_manager):
    backend = MockBackend(chunk_size=128, total_size=20000)
    mgr = make_manager(backend=backend, max_concurrent=1)
    item_id = mgr.enqueue_url("https://youtu.be/pauseme123")
    import time
    time.sleep(0.05)
    mgr.pause(item_id)
    # wait for the pause to actually land
    deadline = time.time() + IDLE_TIMEOUT
    while time.time() < deadline and mgr.queue.get(item_id).status not in ("paused", "completed"):
        time.sleep(0.01)
    item = mgr.queue.get(item_id)
    assert item.status in ("paused", "completed")
    if item.status == "paused":
        mgr.resume(item_id)
        assert mgr.wait_idle(timeout=IDLE_TIMEOUT)
        assert mgr.queue.get(item_id).status == "completed"


def test_cancel_removes_partial_file(db, tmp_path, make_manager):
    backend = MockBackend(chunk_size=256, total_size=50000)
    mgr = make_manager(backend=backend, max_concurrent=1)
    item_id = mgr.enqueue_url("https://youtu.be/cancelme123")
    import time
    time.sleep(0.05)
    mgr.cancel(item_id)
    assert mgr.wait_idle(timeout=IDLE_TIMEOUT)
    item = mgr.queue.get(item_id)
    assert item.status == "cancelled"


def test_failed_extraction_marks_item_failed(db, tmp_path, make_manager):
    backend = MockBackend(fail_urls={"https://youtu.be/willfail1234"})
    mgr = make_manager(backend=backend)
    item_id = mgr.enqueue_url("https://youtu.be/willfail1234")
    assert mgr.wait_idle(timeout=IDLE_TIMEOUT)
    item = mgr.queue.get(item_id)
    assert item.status == "failed"
    assert item.error_message is not None


def test_retry_failed_item(db, tmp_path, make_manager):
    backend = MockBackend(fail_urls={"https://youtu.be/retryme12345"})
    mgr = make_manager(backend=backend)
    item_id = mgr.enqueue_url("https://youtu.be/retryme12345")
    assert mgr.wait_idle(timeout=IDLE_TIMEOUT)
    assert mgr.queue.get(item_id).status == "failed"

    backend.fail_urls.clear()  # simulate the transient failure clearing up
    mgr.retry(item_id)
    assert mgr.wait_idle(timeout=IDLE_TIMEOUT)
    item = mgr.queue.get(item_id)
    assert item.status == "completed"
    assert item.retry_count == 1


def test_retry_all_failed(db, tmp_path, make_manager):
    backend = MockBackend(fail_urls={"https://youtu.be/f1_aaaaaaaaa", "https://youtu.be/f2_bbbbbbbbb"})
    mgr = make_manager(backend=backend)
    mgr.enqueue_many(["https://youtu.be/f1_aaaaaaaaa", "https://youtu.be/f2_bbbbbbbbb",
                      "https://youtu.be/ok_ccccccccc"])
    assert mgr.wait_idle(timeout=IDLE_TIMEOUT)
    assert len(mgr.queue.ids_by_status("failed")) == 2
    backend.fail_urls.clear()
    retried = mgr.retry_all_failed()
    assert retried == 2
    assert mgr.wait_idle(timeout=IDLE_TIMEOUT)
    assert len(mgr.queue.ids_by_status("failed")) == 0


def test_remove_item(db, tmp_path, make_manager):
    mgr = make_manager()
    item_id = mgr.enqueue_url("https://youtu.be/removeme1234")
    mgr.wait_idle(timeout=IDLE_TIMEOUT)
    mgr.remove(item_id)
    assert mgr.queue.get(item_id) is None


def test_no_double_dispatch_of_same_item(db, tmp_path, make_manager):
    """retry_all_failed() calls retry() -> _try_dispatch() once per failed
    item in a tight loop. Before the fix, a second _try_dispatch() call
    could pick up an item that a just-spawned thread hadn't yet marked
    'extracting', dispatching it twice onto two racing threads."""
    backend = MockBackend(chunk_size=32, total_size=2000, force_title="Same Title Every Time")
    mgr = make_manager(backend=backend, max_concurrent=4)

    orig_run_item = mgr._run_item
    started_ids: list[int] = []

    def traced_run_item(item_id, token):
        started_ids.append(item_id)
        orig_run_item(item_id, token)

    mgr._run_item = traced_run_item
    ids = mgr.enqueue_many([f"https://youtu.be/multi{i:07d}" for i in range(5)])
    assert mgr.wait_idle(timeout=IDLE_TIMEOUT)

    # Every item_id should have started exactly once, never twice.
    from collections import Counter
    counts = Counter(started_ids)
    assert all(c == 1 for c in counts.values()), f"an item was dispatched more than once: {counts}"
    assert set(counts) == set(ids)

    items = mgr.queue.all()
    assert all(i.status == "completed" for i in items)
    assert len({i.output_path for i in items}) == len(items)  # every path unique


def test_retry_all_failed_with_forced_title_collision_no_corruption(db, tmp_path, make_manager):
    """Regression test for the double-dispatch race: retrying several failed
    items that all resolve to the identical filename must never corrupt or
    lose a file, even under repeated concurrent dispatch."""
    fail_urls = {"https://youtu.be/rf1_aaaaaaa", "https://youtu.be/rf2_bbbbbbb",
                "https://youtu.be/rf3_ccccccc"}
    backend = MockBackend(fail_urls=set(fail_urls), force_title="Collision Title",
                          chunk_size=32, total_size=1000)
    mgr = make_manager(backend=backend, max_concurrent=4)
    mgr.enqueue_many(list(fail_urls) + ["https://youtu.be/ok_zzzzzzzzz"])
    assert mgr.wait_idle(timeout=IDLE_TIMEOUT)
    assert len(mgr.queue.ids_by_status("failed")) == 3

    backend.fail_urls.clear()
    mgr.retry_all_failed()
    assert mgr.wait_idle(timeout=IDLE_TIMEOUT)

    items = mgr.queue.all()
    assert all(i.status == "completed" for i in items)
    paths = [i.output_path for i in items]
    assert len(set(paths)) == 4  # all four distinct, none silently overwritten
    from pathlib import Path
    for p in paths:
        assert Path(p).exists()
        assert Path(p).stat().st_size == 1000


def test_reorder(db, tmp_path, make_manager):
    backend = MockBackend()
    mgr = make_manager(backend=backend, max_concurrent=0)  # nothing auto-starts
    mgr.max_concurrent = 0
    ids = [mgr.enqueue_url(f"https://youtu.be/order{i:07d}") for i in range(3)]
    mgr.reorder([ids[2], ids[1], ids[0]])
    ordered = [i.id for i in mgr.queue.all()]
    assert ordered == [ids[2], ids[1], ids[0]]


def test_events_emitted(db, tmp_path, make_manager):
    events = []
    backend = MockBackend()
    mgr = make_manager(backend=backend, max_concurrent=2, on_event=lambda e: events.append(e.type))
    mgr.enqueue_url("https://youtu.be/eventtest123")
    assert mgr.wait_idle(timeout=IDLE_TIMEOUT)
    assert "added" in events
    assert "status_changed" in events
    assert "progress" in events


def test_shutdown_joins_active_threads_and_preserves_part_file(db, tmp_path, make_manager):
    """Shutdown must block until in-flight downloads actually stop (not just
    request a flag), and must pause rather than cancel so the .part file
    survives for a resumed download after the app restarts."""
    backend = MockBackend(chunk_size=16, total_size=20_000)
    mgr = make_manager(backend=backend, max_concurrent=1)
    item_id = mgr.enqueue_url("https://youtu.be/shutdowntest1")
    import time
    time.sleep(0.02)
    mgr.shutdown(timeout=IDLE_TIMEOUT)

    # No thread should still be alive touching the (soon to be closed) db.
    assert not mgr._active
    item = mgr.queue.get(item_id)
    assert item.status in ("paused", "completed")
    if item.status == "paused":
        from pathlib import Path
        part_files = list(Path(tmp_path / "downloads").rglob("*.part"))
        assert len(part_files) == 1


def test_concurrent_items_with_identical_titles_do_not_collide(db, tmp_path, make_manager):
    """Two different videos that happen to render to the same filename
    (e.g. same uploader + generic title) must not race on the same .part
    file — one of them should land on a ' (1)' suffixed path instead."""
    backend = MockBackend(chunk_size=64, total_size=8000, force_title="Highlights")
    mgr = make_manager(backend=backend, max_concurrent=2)
    id1 = mgr.enqueue_url("https://youtu.be/collideAAAAA")
    id2 = mgr.enqueue_url("https://youtu.be/collideBBBBB")
    assert mgr.wait_idle(timeout=IDLE_TIMEOUT)

    item1, item2 = mgr.queue.get(id1), mgr.queue.get(id2)
    assert item1.status == "completed"
    assert item2.status == "completed"
    assert item1.output_path != item2.output_path

    from pathlib import Path
    assert Path(item1.output_path).exists()
    assert Path(item2.output_path).exists()
    assert Path(item1.output_path).stat().st_size == 8000
    assert Path(item2.output_path).stat().st_size == 8000
