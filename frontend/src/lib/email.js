import nodemailer from 'nodemailer';
import {
    VERIFICATION_EMAIL_TEMPLATE,
    PASSWORD_RESET_REQUEST_TEMPLATE,
    PASSWORD_RESET_SUCCESS_TEMPLATE,
    WELCOME_EMAIL_TEMPLATE,
    INVITATION_EMAIL_TEMPLATE
} from './emailTamplets.js';

const transporter = nodemailer.createTransport({    
    service: process.env.EMAIL_SERVICE || 'gmail',
    auth: {
        user: process.env.GMAIL_USERNAME,
        pass: process.env.GMAIL_PASSWORD,
    },
});

const sender = {
    email: process.env.GMAIL_USERNAME,
    name: process.env.MAIL_SENDER_NAME || 'ED-TECH',
};

const sendEmail = async (to, subject, htmlBody, category) => {
    try {
        const mailOptions = {
            from: `"${sender.name}" <${sender.email}>`,
            to: to,
            subject: subject,
            html: htmlBody,
            headers: { 'X-App-Category': category },
        };

        const info = await transporter.sendMail(mailOptions);
        console.log(`Email sent successfully: "${subject}" to ${to} (Category: ${category})`);
        return info;
    } catch (error) {
        console.error(`Error sending email: "${subject}" to ${to} (Category: ${category})`, error);
        throw error;
    }
};

export const sendVerificationEmail = async (email, verificationUrl) => {
    const subject = "Verify your email - ED-TECH";
    const htmlBody = VERIFICATION_EMAIL_TEMPLATE.replace('{verificationUrl}', verificationUrl);
    const category = "Email verification";

    await sendEmail(email, subject, htmlBody, category);
};

export const sendWelcomeEmail = async (email, name) => {
    const subject = "Welcome to ED-TECH!";
    const htmlBody = WELCOME_EMAIL_TEMPLATE.replace('{userName}', name || 'there');
    const category = "Welcome Email";

    await sendEmail(email, subject, htmlBody, category);
};

export const sendResetPasswordEmail = async (email, resetURL) => {
    const subject = "Reset your password - ED-TECH";
    const htmlBody = PASSWORD_RESET_REQUEST_TEMPLATE.replace('{resetURL}', resetURL);
    const category = "Password reset request";

    await sendEmail(email, subject, htmlBody, category);
};

export const sendPasswordResetSuccessEmail = async (email) => {
    const subject = "Password reset successful - ED-TECH";
    const htmlBody = PASSWORD_RESET_SUCCESS_TEMPLATE;
    const category = "Password reset success";

    await sendEmail(email, subject, htmlBody, category);
};

export const sendInvitationEmail = async (email, invitationToken) => {
    const subject = "Invitation to join ED-TECH";
    const htmlBody = INVITATION_EMAIL_TEMPLATE.replace('{invitationToken}', invitationToken);
    const category = "Invitation Email";

    await sendEmail(email, subject, htmlBody, category);
};