import type { Locale } from '../config';
import type { Dictionary } from './en';
import ar from './ar';
import de from './de';
import en from './en';
import es from './es';
import fr from './fr';
import hi from './hi';
import id from './id';
import it from './it';
import ja from './ja';
import ko from './ko';
import nl from './nl';
import pl from './pl';
import pt from './pt';
import ro from './ro';
import ru from './ru';
import tr from './tr';
import uk from './uk';
import zh from './zh';

export type { Dictionary };

export const dictionaries: Record<Locale, Dictionary> = {
  ro, en, es, fr, de, it, pt, pl, nl, ru, uk, tr, ar, hi, zh, ja, ko, id,
};
