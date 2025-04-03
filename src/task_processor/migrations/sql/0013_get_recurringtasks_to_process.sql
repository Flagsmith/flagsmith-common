CREATE OR REPLACE FUNCTION get_recurringtasks_to_process()
RETURNS SETOF task_processor_recurringtask AS $$
DECLARE
    row_to_return task_processor_recurringtask;
BEGIN
    -- Select the tasks that needs to be processed
    FOR row_to_return IN
        SELECT *
        FROM task_processor_recurringtask
        -- Add one minute to the timeout as a grace period for overhead
        WHERE is_locked = FALSE OR (locked_at IS NOT NULL AND locked_at < NOW() - timeout + INTERVAL '1 minute')
        ORDER BY last_picked_at NULLS FIRST
        LIMIT 1
        -- Select for update to ensure that no other workers can select these tasks while in this transaction block
        FOR UPDATE SKIP LOCKED
    LOOP
        -- Lock every selected task(by updating `is_locked` to true)
        UPDATE task_processor_recurringtask
        -- Lock this row by setting is_locked True, so that no other workers can select these tasks after this
        -- transaction is complete (but the tasks are still being executed by the current worker)
        SET is_locked = TRUE, locked_at = NOW(), last_picked_at = NOW()
        WHERE id = row_to_return.id;
        -- If we don't explicitly update the columns here, the client will receive a row
        -- that is locked but still shows `is_locked` as `False` and `locked_at` as `None`.
        row_to_return.is_locked := TRUE;
        row_to_return.locked_at := NOW();
        RETURN NEXT row_to_return;
    END LOOP;

    RETURN;
END;
$$ LANGUAGE plpgsql

