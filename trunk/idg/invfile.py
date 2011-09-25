# Invariant File abstraction
# -*- coding: utf-8 -*-

import os.path as path
import re

from file import File
import util.logger
import util.clock

log = util.logger.getlog('idg.invfile')

class InvFile(File):
    """@brief Class to manage Daikon outputs containing invariants.

    Holds the invariants in a dictionary-like structure:
        { sequence :
                    [ (name, value),
                      (name, value),
                      (name, value)]
        }

    Invariants within a sequence are ordered alphabetically.
    Includes the necessary logic for differences calculation. 
    """

    _inv_separator = "=" * 75

    _inv_cmp = ["one of", "==", "<=", ">=", "!="]
    _inv_regexp_str = "(?P<name>.+) (?P<sep>%s) (?P<value>.+)"\
            % "|".join(_inv_cmp)
    _inv_regexp = re.compile(_inv_regexp_str)

    def __init__(self, path_):
        super(InvFile, self).__init__(path_)
        self.invs = {}
        self.parse()

    def parse(self):
        """@brief Reads the file and initializes the invariants dict"""
        self.open()

        log.debug("Parsing: " + self._path)

        # Discard the begining of the file.
        for line in self._file:
            if line.startswith(self._inv_separator):
                break

        # Parse output for invariants
        self.invs.clear()
        sequence = ""
        for line in self._file:

            # If there's no sequence set means the begining of one.
            if not sequence:
                sequence = line.split('.')[1]
                log.debug("New sequence: " + sequence)
                self.invs[sequence] = []

            # End of the sequence.
            if line.startswith(self._inv_separator):
                # Close actual sequence.
                if sequence:
                    sequence = ""

            # EOF
            elif line == "Exiting Daikon.":
                break

            # Invariant within a sequence or EOF
            else:
                if sequence:
                    try:
                        name, sep, value = self._split_invariant(line)
                    except ValueError:
                        continue
                    except TypeError:
                        continue

                    log.debug("New Invariant: %s: %s - %s - %s" %
                              (sequence, name, sep, value))

                    self.invs[sequence].append((name, sep, value))

        for sequence in self.invs.keys():
            self.invs[sequence].sort()

    @staticmethod
    def get_time(path_):
        """@brief Extracts the time from the filename."""
        try:
            time = path.basename(path_).split('-')[1].rsplit('.', 1)[0]
        except IndexError:
            return ""
        else:
            return util.clock.min_format(float(time))

    def ninvs(self):
        """@returns the number of invariants"""
        n = 0
        for seq, invs in self.invs.iteritems():
            n += len(invs)

        return n

    def diff(self, inv_file):
        """@brief Computes the differences against another invariant file.

            @param inv_file Another invariant file.
            @returns A dictionary-like structure with instructions to recompose
            the two views of the diff.
            Eg:
                {
                  sequence: {
                      name:'seq', 
                      mode: '+|-|n|c', 
                      list: [(+, inv), (c, inv), ..]
                    }
                }
                """

        # First pass self -> other
        diff = {}

        left_seqs = set(self.invs.keys())
        right_seqs = set(inv_file.invs.keys())

        new_seqs = right_seqs - left_seqs
        removed_seqs = left_seqs - right_seqs
        common_seqs = left_seqs.intersection(right_seqs)

        for seq in left_seqs.union(right_seqs):
            diff[seq] = {}

        # Sequence in right but not in left. (+, new)
        for seq in new_seqs:
            diff[seq]['mode'] = '+'
            diff[seq]['list'] = [('+', inv) for inv in inv_file.invs[seq]]

        # Sequence in left but not in right. (-, removed)
        for seq in removed_seqs:
            diff[seq]['mode'] = '-'
            diff[seq]['list'] = [('-', inv) for inv in self.invs[seq]]

        # Sequence in left and in right. (c, changed)
        for seq in common_seqs:
            diff[seq] = {'list': []}

            # Detect unchanged invariants
            left_invs = set(self.invs[seq])
            right_invs = set(inv_file.invs[seq])
            common_invs = left_invs.intersection(right_invs)

            # Add unchanged invariants
            diff[seq]['list'].extend([('n', inv) for inv in common_invs])

            # If the complete sequence is unchanged, we're done.
            if len(common_invs) == len(left_invs) == len(right_invs):
                diff[seq]['mode'] = 'n'
                continue

            # Otherwise, the sequence is changed.
            diff[seq]['mode'] = 'c'

            # Avoid compare again unchanged invariants
            left_invs -= common_invs
            right_invs -= common_invs

            repeated_invs = set()

            # Find each different invariant by name an separator.
            # left vs right
            for self_inv in left_invs: 
                found = False
                for other_inv in right_invs: 

                    found = (self_inv[:2] == other_inv[:2])
                    found = found and self_inv not in repeated_invs
                    found = found and other_inv not in repeated_invs

                    # Same name and sep but different value (c, change)
                    if found: 
                        diff[seq]['list'].append(('c', self_inv, other_inv))
                        repeated_invs.add(self_inv)
                        repeated_invs.add(other_inv)
                        break

                # Not found (-, deleted) 
                if not found and self_inv not in repeated_invs:
                    diff[seq]['list'].append(('-', self_inv))

            # Second pass for new invariants.
            # other vs self
            for other_inv in right_invs:
                found = False

                for self_inv in left_invs:
                    found = self_inv[:2] == other_inv[:2]
                    found = found and self_inv not in repeated_invs
                    found = found and other_inv not in repeated_invs

                    # Same name and sep but different value (c, change)
                    if found:
                        diff[seq]['list'].append(('c', self_inv, other_inv))
                        repeated_invs.add(self_inv)
                        repeated_invs.add(other_inv)
                        break

                # Not found (+, new) 
                if not found and other_inv not in repeated_invs:
                    diff[seq]['list'].append(('+', other_inv))

        log.debug(diff)
        return diff

    def _split_invariant(self, invariant):
        """@brief splits an invariant in two parts with a separator.
        @returns name, separator and value. None in case of error.
        """
        m = self._inv_regexp.match(invariant)

        if not m:
            return None

        return m.group('name', 'sep', 'value')
