import { nextCookies } from "better-auth/next-js";
import { createAuthClient } from "better-auth/client";
import { inferAdditionalFields } from "better-auth/client/plugins";

export const authClient = createAuthClient({
    plugins: [
        inferAdditionalFields,
        nextCookies()
    ],
})