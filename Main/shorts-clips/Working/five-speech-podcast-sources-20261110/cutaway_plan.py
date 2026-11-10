"""Source-library candidates and dialogue cues for private review."""

# The source offset and horizontal crop are checked against the candidate frames.
CUTS = {
    "01": [
        (2.34, 3.93, "Breaking Bad - Walter White S05A", "hands-at-a-breakfast-plate", .12, .50, "A plate makes the opening anecdote tangible."),
        (4.34, 6.20, "Iron Man", "tony-in-front-of-a-holographic-workbench", .12, .55, "A deliberately arranged workspace visualizes planning the work."),
        (7.58, 10.94, "Breaking Bad - Walter White S05A", "two-men-work-at-a-kitchen-counter", .16, .51, "A kitchen work surface illustrates mise en place and the routine of service."),
        (13.88, 15.66, "Breaking Bad - Walter White S05A", "hands-at-work-in-low-light", .12, .54, "A close view of practiced hands follows the promotion line."),
        (20.18, 23.32, "Iron Man", "tony-works-at-a-crowded-bench", .15, .50, "Efficient hands at a work station underline the empty-handed rule."),
        (25.36, 27.19, "Iron Man", "walking-across-the-hangar", .1, .54, "A larger workplace sets up the transition to the CEO line."),
    ],
    "02": [
        (2.78, 4.89, "Peaky Blinders - Tommy Shelby S04", "boxing-ring-from-the-crowd", .12, .51, "The ring gives the match count a competitive visual as the opening question clears."),
        (7.66, 8.86, "Jon Snow", "crowd-forms-around-jon", .14, .50, "The spectators suggest the public result after the percentage reveal."),
        (11.28, 12.84, "Jon Snow", "jon-braces-against-a-sword-strike", .1, .55, "An individual exchange puts the question about points in visual terms."),
        (20.01, 23.79, "Jon Snow", "wide-shot-of-sparring-in-the-yard", .08, .50, "Even skilled competitors must respond to repeated exchanges."),
        (26.35, 28.47, "Jon Snow", "jon-gets-back-up-in-training", .0, .47, "A setback followed by getting up illustrates losing a point and moving on."),
        (33.31, 34.67, "Jon Snow", "sparring-partners-square-up-again", .12, .50, "The fighters reset on the double-fault line before the speaker delivers the takeaway."),
    ],
    "03": [
        (3.0, 5.63, "Peaky Blinders - Tommy Shelby S04", "tommy-alone-in-the-office", .18, .43, "The desk illustrates the conventional career beat after his opening call for purpose."),
        (6.52, 8.81, "Peaky Blinders - Tommy Shelby S06", "figure-walks-across-the-grass", .15, .52, "The open landscape widens the frame as he says purpose crosses disciplines."),
        (10.64, 12.24, "Iron Man", "yinsen-works-at-the-bench", .1, .50, "Focused work gives the abstract word purpose a human action."),
        (14.42, 15.72, "Peaky Blinders - Tommy Shelby S06", "tommy-in-a-sunlit-close-up", .16, .50, "A still moment of reflection accompanies the thought about one's place in time."),
        (21.42, 23.40, "Peaky Blinders - Tommy Shelby S04", "silhouette-in-the-lit-doorway", .18, .50, "Crossing a threshold represents choosing a path."),
        (23.40, 26.72, "Peaky Blinders - Tommy Shelby S04", "figure-walking-through-sparks", .19, .48, "The difficult walk gives the career struggle a concrete visual before his final line."),
    ],
    "04": [
        (1.77, 4.21, "Iron Man", "yinsen-works-at-the-bench", .13, .50, "Show hands creating something on the first claim about what he makes."),
        (4.97, 5.99, "Iron Man", "tony-in-front-of-a-holographic-workbench", .17, .55, "A design taking shape represents a thing that does not exist yet."),
        (5.99, 7.23, "Iron Man", "prototype-suit-stands-in-the-workshop", .10, .52, "The imagined thing takes on a concrete form."),
        (9.23, 10.51, "Iron Man", "two-figures-in-the-workshop", .12, .46, "The work still has to be done before the idea can exist."),
        (10.51, 12.41, "Iron Man", "tony-alone-in-a-wide-workshop", .15, .62, "The workshop delivers the action in so I'll make it."),
        (15.59, 18.11, "Iron Man", "tony-works-at-a-crowded-bench", .20, .50, "The quiet craft prepares the return to Rubin for I love this thing."),
    ],
    "05": [
        (2.34, 4.40, "Iron Man", "pepper-helps-tony-in-the-lab", .18, .49, "Accepting help makes asking for it concrete before the personal example."),
        (6.30, 8.14, "Avengers Endgame - Steve Rogers", "steve-alone-in-an-indoor-space", .15, .50, "Isolation illustrates the struggle the friend has been carrying."),
        (11.50, 14.24, "Avengers Endgame - Steve Rogers", "two-people-on-a-bench-outside", .14, .50, "A quiet conversation carries the friend's admission and the response."),
        (14.24, 15.18, "Iron Man", "pepper-and-tony-in-quiet-conversation", .16, .65, "A hesitant look illustrates the fear of being a bother."),
        (22.56, 25.82, "Fight Club", "embrace-at-the-support-group", .15, .50, "The embrace illustrates the honor of showing up for someone."),
        (29.40, 30.66, "Avengers Endgame - Steve Rogers", "bucky-listens-in-the-woods", .20, .50, "A friend's attentive reaction accompanies his definition of friendship."),
    ],
}
