package app.namaz.azan.data

/**
 * Who made this, and where to find them.
 *
 * Every line here is taken from the site itself (zero-vast.vercel.app) rather than
 * written from memory. The rules this project has always held for marketing work
 * apply just as much inside the app: no invented metrics, no "trusted by", no
 * client counts, no testimonial. What the site actually says is that it is one
 * independent developer in Khammam, Telangana, writing HTML, CSS and JavaScript by
 * hand, with no framework unless the problem needs one.
 *
 * Kept as constants so the card, the settings row and the link handler cannot
 * drift apart.
 */
object Credits {

    /** The address exactly as it is used in the films' end cards. */
    const val WEBSITE = "https://zero-vast.vercel.app"

    /** Display form, without the scheme — easier to read, same target. */
    const val WEBSITE_LABEL = "zero-vast.vercel.app"

    const val STUDIO = "ZeroVast"

    /** The site's own description of itself, shortened, not paraphrased into a claim. */
    const val TAGLINE = "Websites built to perform."

    const val BYLINE = "Independent web developer · Khammam, Telangana"

    /** "Made by" — used on the home screen card. */
    const val MADE_BY = "This app was built by ZeroVast."

    /** The capabilities, straight from the site's own list. */
    val CAPABILITIES = listOf(
        "Hand-written HTML, CSS and JavaScript",
        "No framework unless the problem needs one",
        "WCAG 2.2 AA accessibility",
        "Core Web Vitals budgets on every build"
    )
}
