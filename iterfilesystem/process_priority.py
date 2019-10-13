import logging

import psutil

log = logging.getLogger()


def set_high_priority():
    p = psutil.Process()
    try:
        old_ionice = p.ionice()

        if psutil.LINUX:
            p.ionice(psutil.IOPRIO_CLASS_BE, value=0)
        else:
            # Windows
            p.ionice(psutil.IOPRIO_HIGH)

        new_ionice = p.ionice()
    except Exception as err:
        log.warning('Can not change ionice: %s', err)
    else:
        log.info('Set higher ionice priority (%s to %s)', old_ionice, new_ionice)

    try:
        old_nice = p.nice()

        if psutil.LINUX:
            p.nice(-10)
        else:
            # Windows
            p.nice(psutil.HIGH_PRIORITY_CLASS)

        new_nice = p.nice()
    except Exception as err:
        log.warning('Can not change nice: %s', err)
    else:
        log.info('Set higher nice priority (%s to %s)', old_nice, new_nice)


def set_low_priority():
    p = psutil.Process()
    try:
        old_ionice = p.ionice()

        if psutil.LINUX:
            p.ionice(psutil.IOPRIO_CLASS_IDLE)
        else:
            # Windows
            p.ionice(psutil.IOPRIO_LOW)

        new_ionice = p.ionice()
    except Exception as err:
        log.warning('Can not change ionice: %s', err)
    else:
        log.info('Set lower ionice priority (%s to %s)', old_ionice, new_ionice)

    try:
        old_nice = p.nice()

        if psutil.LINUX:
            p.nice(10)
        else:
            # Windows
            p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)

        new_nice = p.nice()
    except Exception as err:
        log.warning('Can not change nice: %s', err)
    else:
        log.info('Set lower nice priority (%s to %s)', old_nice, new_nice)
