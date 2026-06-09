import { PrismaClient } from '@prisma/client';
const prisma = new PrismaClient();

async function main() {
  await prisma.whitelist.upsert({
    where: { discordId: '903327749534523452' },
    update: {},
    create: {
      discordId: '903327749534523452',
      addedBy: '903327749534523452',
      role: 'owner',
      reason: 'Bot owner',
    },
  });

  await prisma.user.upsert({
    where: { discordId: '903327749534523452' },
    update: { isWhitelisted: true, isBotOwner: true },
    create: {
      discordId: '903327749534523452',
      username: 'owner',
      isWhitelisted: true,
      isBotOwner: true,
    },
  });

  console.log('Owner whitelisted successfully');
  await prisma.$disconnect();
}

main();
